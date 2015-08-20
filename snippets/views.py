from py2neo import Node, Relationship, Graph, neo4j
from django.db import models
from models import WordCard
from rest_framework import status
from rest_framework.decorators import list_route
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from serializers import WordCardSerializer
from django.conf import settings
from collections import OrderedDict
import traceback
import sys,inspect
import staticpaths
from pywsd.similarity import max_similarity as maxsim
import nltk


class HelpViewSet(viewsets.ViewSet):
    
    @list_route(methods=['get'])
    def list_apis(self,request):
        print __name__
        classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        apis=None
        print dir(sys.modules[__name__])
        
        for aclass in classes:
            if aclass[1].__module__ != __name__:
                continue
            methods=inspect.getmembers(aclass[1], predicate=inspect.ismethod)
            for method in methods:
                print method[1].__dict__
                if 'bind_to_methods' in method[1].__dict__ :
                    if apis is None:
                        apis=[]
                    apis.append(method[1].__name__)
        return Response({'Available API':apis}) 
        

def api_marker_decorator(view_method):
    # mark the method as something that requires view's class
    view_method.is_api = True
    return view_method

class LookupWordRelationViewSet(viewsets.ViewSet):

    @api_marker_decorator
    @list_route(methods=['get'])
    def find_similarity(self,request):
        words=str(request.GET['words']).split(',')
        start_word=words[0]
        end_word=words[1]
        arg3=request.GET['relationstouse']
        rels_to_use=None
        if arg3 is not None and str(arg3) == "all" :
            rels_to_use='*'
        elif arg3 is not None and str(arg3) != "" :
            rels_to_use=":"+arg3.replace('_','|:')+"*"
        if start_word ==None or end_word==None:
            print("Please specify both the words.")
            return False
        paths=[]
        if request.method=='GET':
            graph=LookupWordViewSet.connect_to_neo()
            if rels_to_use is not None :
                q=r"match (n {name:'"+start_word+"'}), (m {name:'"+end_word+"'}), p=allShortestPaths((n)-["+rels_to_use+"]->(m)) return relationships(p)"
            else:
                print('Problem with the valdity of the input parameters. Please contact the programmer.')
            print q
            results=graph.cypher.execute(q)
            for result in results:
                path={}
                relations=result[0]
                if len(relations) >0:
                    path['start_word']=start_word
                    path['end_word']=end_word                
                for relation in relations:
                    if 'subpaths' not in path:
                        path['subpaths']=[]    
                    r=OrderedDict({})
                    r['from']=relation.start_node.properties['name']
                    r['to']=relation.end_node.properties['name']
                    r['definition']=relation.properties['definition']
                    r['part_of_speech']=relation.properties['pos']
                    r['relation']=relation.type
                    examples=relation.properties['example']
                    if examples:
                        r['examples']=examples
                
                    path['subpaths'].append(r)
                paths.append(path)
        return Response(paths)
    

        

    @staticmethod  
    def connect_to_neo():
        try:
            graph= Graph("http://"+settings.NEO4J_DATABASES['default']['USER']+":"+settings.NEO4J_DATABASES['default']['PASSWORD']+"@"+settings.NEO4J_DATABASES['default']['HOST']+":"+str(settings.NEO4J_DATABASES['default']['PORT'])+settings.NEO4J_DATABASES['default']['ENDPOINT'])
            return graph
        except:
            print(traceback.format_exc())    
            return False

class LookupWordViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for lookip up word details
    """
    @api_marker_decorator    
    @list_route(methods=['get'])
    def group_by_relation(self, request):

        if request.method=='GET':
            word=request.GET['word']
            rels=request.GET['lookup']            
            rels_list=rels.split('_')
            if len(rels_list) ==0:
                print ('No relations specified')
            elif rels != 'all':
                construction=""
                for rel in rels_list:
                    construction=construction+":"+rel+'|'
                dict_of_details=(LookupWordViewSet.find_and_group_by_relation(word,construction[:-1]))
            else:
                dict_of_details=(LookupWordViewSet.find_and_group_by_relation(word,''))
            wordcard = WordCard(word=word,dictdetails=dict_of_details)
            print dict_of_details
        else:
            print('Http method not supported in this version.')
        return Response(dict_of_details)

    @api_marker_decorator
    @list_route(methods=['get'])
    def group_by_definition(self, request):
        if request.method=='GET':
            word=request.GET['word']
            rels=request.GET['lookup']        
            rels_list=rels.split('_')
            if len(rels_list) ==0:
                print ('No relations specified')
            elif rels != 'all':
                construction=""
                for rel in rels_list:
                    construction=construction+":"+rel+'|'
                dict_of_details=(LookupWordViewSet.find_and_group_by_definition(word,construction[:-1]))
            else:
                dict_of_details=(LookupWordViewSet.find_and_group_by_definition(word,''))
                wordcard = WordCard(word=word,dictdetails=dict_of_details)
        else:
            print('Http method not supported in this version.')
        return Response(dict_of_details)

    @staticmethod
    def get_pronunciation_url(word):
        return str(staticpaths.URL_FOR_PRONUNICATION_FILES)+word+'.mp3'

    @staticmethod
    def get_corpus_for_examples():
        return str(staticpaths.CORPUS_FOR_EXAMPLES)
        
    @staticmethod
    def find_and_group_by_relation(word,relation):
        graph=LookupWordViewSet.connect_to_neo()
        q=r"match(n {name:'"+word.replace("'","\\\'")+"'})-[r"+relation+"]->(m) return type(r),r,m"
        edges=graph.cypher.execute(q)
        edge_senses={}
        edge_senses['word']=word
        edge_senses['pronunciation_url']=LookupWordViewSet.get_pronunciation_url(word)        
        i=-1
        while i < len(edges)-1:
            i=i+1
            edge=edges[i]
            relationship_type=edge[0]
            relationship=edge[1]
            node=edge[2]
            if node.properties['name'] == word:
                continue
            definition=relationship.properties['definition']
            if relationship_type not in edge_senses.keys():
                edge_senses[relationship_type]={}
            if definition not in edge_senses[relationship_type].keys():
                edge_senses[relationship_type][definition]=[]
            edge_senses[relationship_type][definition].append([node.properties['name'],relationship.properties['pos']])
        return edge_senses
        
    @staticmethod
    def find_and_group_by_definition(word,relation):
        graph=LookupWordViewSet.connect_to_neo()
        q=r"match(n {name:'"+word.replace("'","\\\'")+"'})-[r"+relation+"]->(m) return type(r),r,m"
        edges=graph.cypher.execute(q)
        edge_senses={}
        edge_senses['word']=word
        edge_senses['pronunciation_url']=LookupWordViewSet.get_pronunciation_url(word)

        i=-1
        while i < len(edges)-1:
            i=i+1
            edge=edges[i]
            relationship_type=edge[0]
            relationship=edge[1]
            node=edge[2]
            if node.properties['name'] == word:
                continue
            definition=relationship.properties['definition']
            if definition not in edge_senses.keys():
                edge_senses[definition]={}
            if relationship_type not in edge_senses[definition].keys():
                edge_senses[definition][relationship_type]=[]
            edge_senses[definition][relationship_type].append([node.properties['name'],relationship.properties['pos']])
        return edge_senses
    

#    @api_marker_decorator
#    @list_route(methods=['get'])
    def find_pos(self, request,arg1=None,arg2=None):
        word=arg1
        rels=arg2
        if request.method=='GET':
            rels_list=rels.split('_')
            if len(rels_list) ==0:
                print ('No relations specified')
            else:
                construction=""
                for rel in rels_list:
                    construction=construction+":"+rel+'|'
                dict_of_details=(LookupWordViewSet.find_and_group_by_relation(word,construction[:-1]))
                wordcard = WordCard(word=word,dictdetails=dict_of_details)
                print wordcard.dictdetails
#                renderedjson = JSONRenderer().render(serializer.data)
            print dict_of_details
        else:
            print('Http method not supported in this version.')
        return Response(dict_of_details)
        

    @api_marker_decorator    
    @list_route(methods=['get'])
    def find_examples(self, request):
        query_parameters=request.GET
        print query_parameters
        word=query_parameters.getlist('word')[0]
        definition=None
        corpus_for_examples=None
        print query_parameters.getlist('corpus_to_use')[0]
        try:
            corpus_for_examples=query_parameters.getlist('corpus_to_use')[0]
        except :
            print('Corpus_for_example not specified.')
        try:
            definition=query_parameters.getlist('definition')[0]
        except :
            print('Definition not specified.')


        if word ==None:
            return Response('Some problem with the parameters pass with GET request')
        else:
            graph=LookupWordViewSet.connect_to_neo()
        try:
            examples={}
            q=r"match (n {name:'"+word.replace("'","\\\'")+"'})-[r:synonym]->(m) return r,m "
            results=graph.cypher.execute(q)
            for result in results:
                synonym=result[0]
                definition=synonym.properties['definition']
                if synonym.properties['example']:
                    end_word=result[1].properties['name']    
                    if definition not in examples:
                        examples[definition]={}                
                    if end_word not in examples[definition]:
                        examples[definition][end_word]=set()
                    examples[definition][end_word].add(synonym.properties['example'])
                if corpus_for_examples is not None and synonym.properties[str(corpus_for_examples)+'_examples']:
                    end_word=result[1].properties['name']    
                    if definition not in examples:
                        examples[definition]={}                
                    if end_word not in examples[definition]:
                        examples[definition][end_word]=set()
                    examples[definition][end_word]=examples[definition][end_word].union(synonym.properties[str(corpus_for_examples)+'_examples'])
        except :
            print(traceback.format_exc())            
            print('Http method not supported in this version.')
        return Response(examples)


        

    @staticmethod  
    def connect_to_neo():
        try:
            graph= Graph("http://"+settings.NEO4J_DATABASES['default']['USER']+":"+settings.NEO4J_DATABASES['default']['PASSWORD']+"@"+settings.NEO4J_DATABASES['default']['HOST']+":"+str(settings.NEO4J_DATABASES['default']['PORT'])+settings.NEO4J_DATABASES['default']['ENDPOINT'])
            return graph
        except:
            print(traceback.format_exc())    
            return False

