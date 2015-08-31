from py2neo import Node, Relationship, Graph, neo4j
from py2neo.server import GraphServer
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
from pywsd import disambiguate
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
                if 'bind_to_methods' in method[1].__dict__ :
                    description=method[1].__doc__
                    if apis is None:
                        apis=[]
                    apis.append({'API_name':method[1].__name__,'description':description})
        return Response({'Available API':apis}) 
        

def api_marker_decorator(view_method):
    # mark the method as something that requires view's class
    view_method.is_api = True
    return view_method

class LookupWordRelationViewSet(viewsets.ViewSet):

    @api_marker_decorator
    @list_route(methods=['get'])
    def find_similarity(self,request):
        """
        ENDPOINT:/v1/wordnet/find_similarity
        PARAMETERS:1.  <words> is a comma-separated pair of words which is of the form <start_word>,<end_word>.
                   2.  <relationstouse> specifies the relations which are to be used for finding the relation of the second word with respect to the first word. Multiple relation types are specified by using the underscore character as the concatenating character. For example, to look for relations between the two words using only synonyms and antonyms, we need to specify the value of relationstouse as 'synonym_antonym'. If we want to use all of the available relation types for finding the relation between the two words, we specify the value of relationstouse as 'all'. Any of the relation types specified in the first API can be used for finding the relation between the two words. 

        """
        server=LookupWordViewSet.get_neo_server()
        LookupWordViewSet.start_neo('/home/snehal/data/sensegraph.db',server)     
        graph=LookupWordViewSet.connect_to_neo()
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
                q=r"match (n:word {name:'"+start_word+"'}), (m:word {name:'"+end_word+"'}),(n)-[r1:synonym]->(k1:sense), (m)-[r2:synonym]->(k2:sense), p=shortestPath((k1)-[r"+rels_to_use+"]-(k2)) with nodes(p) as pnodes, k1 , k2 return k1,pnodes,k2 limit 2"
            else:
                print('Problem with the valdity of the input parameters. Please contact the programmer.')
            print q
            results=graph.cypher.execute(q)
            print results
            for result in results:
                path={}
                start_sense=result[0]
                end_sense=result[2]
                path_nodes=result[1]
                if len(path_nodes) >0:
                    path['start_word']=start_word
                    path['end_word']=end_word                
                for node in path_nodes:
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
        """
        ENDPOINT:/v1/wordnet/group_by_relation
        DESCRIPTION: This API returns related words, grouped by the various relation types found for the specified word.
        PARAMETERS:1.  <word> is the specified word. Wordnet supports common word usages like 'use up', 'give in', etc. Hence such usages, involving spaces should be transformed into a single string, with each space replace by an underscore. For example, the usage 'use up' should instead be looked up by specifying the value of the parameter word as 'use_up'.
                   2.  <lookup> specifies the relations which are to be used for finding the relation of the second word with respect to the first word. Multiple relation types are specified by using the underscore('_') as the concatenating character. For example, to look for relations between the two words using only synonyms and antonyms, we need to specify the value of lookup as 'synonym_antonym'. If we want to use all of the available relation types for finding the relation between the two words, we specify the value of lookup as 'all'. Any of the relation types specified in the first API can be used for finding the relation between the two words.
        """
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
        """
        ENDPOINT:/v1/wordnet/group_by_definition
        DESCRIPTION: This API returns related words, grouped by the various definitions found for the specified word. 
        PARAMETERS:1.  <word> is the specified word. Wordnet supports common word usages like 'use up', 'give in', etc. Hence such usages, involving spaces should be transformed into a single string, with each space replace by an underscore. For example, the usage 'use up' should instead be looked up by specifying the value of the parameter word as 'use_up'.
                   2.  <lookup> specifies the relations which are to be used for finding the relation of the second word with respect to the first word. Multiple relation types are specified by using the underscore('_') as the concatenating character. For example, to look for relations between the two words using only synonyms and antonyms, we need to specify the value of lookup as 'synonym_antonym'. If we want to use all of the available relation types for finding the relation between the two words, we specify the value of lookup as 'all'. Any of the relation types specified in the first API can be used for finding the relation between the two words.
        """

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
        server=LookupWordViewSet.get_neo_server()
        LookupWordViewSet.start_neo('/home/snehal/data/graphwithoutexamples.db',server)     
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
        server=LookupWordViewSet.get_neo_server()
        LookupWordViewSet.start_neo('/home/snehal/data/graphwithoutexamples.db',server)     
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
        """
        ENDPOINT:/v1/wordnet/find_examples
        DESCRIPTION:This API extracts sentences from the specified corpus, which are examples of the specified word. The grouping in this case is by definitions by default.
        PARAMETERS:1.   <word> is the specified word whose examples we are looking for. 
                   2.   <corpus_to_use> is the corpus, specified, from which we want to extract examples for the specified word.
                   3.   <definition> is an optional parameter which is used to seek examples which have the specified word used in only a particular sense. TODO.
        """
        query_parameters=request.GET
        print query_parameters
        word=query_parameters.getlist('word')[0]
        definition=None
        corpus_for_examples=None
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
            try:
                graph=LookupWordViewSet.connect_to_neo()
            except:
                LookupWordViewSet.start_neo('/home/snehal/data/examplesentencesgraph.db',server)
                
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
    def get_neo_server():
        try:
            server = GraphServer(staticpaths.NEO4J_SERVER_DIST_PATH)
            return server
        except:
            print(traceback.format_exc())    
            print('Could not find and initialize the neo4j server')    
            return False


    @staticmethod
    def start_neo(db_dump_location='graph.db',server=None):
        print str(server.pid) + ' PIDDDDDDDDD '
        if server.pid is None:
            try:
                server.start()
            except:
                print('Some issue in server start.')
        else:
            print('A server process is already running. Checking for the graph location in use....')
            if server.conf.get('neo4j-server','org.neo4j.server.database.location') !=db_dump_location:
                # set the name of the graph db dump location
                try:
                    server.stop()
                    server.update_server_properties(database_location=db_dump_location)
                    server.start()
                    print('neo4j server has been successfully started.')
                except:
                    print('Some issue in setting the db dump location. Defaulting to '+str(server.conf.get('neo4j-server','org.neo4j.server.database.location')))
                

    @staticmethod
    def stop_neo(server):
        try:
            server.stop()
        except:
            print(traceback.format_exc())    
            print('error in stoping')



    @staticmethod  
    def connect_to_neo():
        try:
            graph= Graph("http://"+settings.NEO4J_DATABASES['default']['USER']+":"+settings.NEO4J_DATABASES['default']['PASSWORD']+"@"+settings.NEO4J_DATABASES['default']['HOST']+":"+str(settings.NEO4J_DATABASES['default']['PORT'])+settings.NEO4J_DATABASES['default']['ENDPOINT'])
            return graph
        except:
            print(traceback.format_exc())    
            return False
            
            
            
            
            
            
            
            
            
            
            
    @api_marker_decorator    
    @list_route(methods=['get'])
    def find_ungrouped_examples(self, request):
        """
        ENDPOINT:/v1/wordnet/find_ungrouped_examples
        DESCRIPTION:This API extracts sentences from the specified corpus, which are examples of the specified word. 
        PARAMETERS:1.   <word> is the specified word whose examples we are looking for. 
                   2.   <corpus_to_use> is the corpus, specified, from which we want to extract examples for the specified word. TODO
                   3.   <definition> is an optional parameter which is used to seek examples which have the specified word used in only a particular sense. TODO.
        """
        query_parameters=request.GET
        word=query_parameters.getlist('word')[0]
        definition=None
        corpus_for_examples=None
        try:
            corpus_for_examples=query_parameters.getlist('corpus_to_use')[0]
        except :
            print('Corpus_for_example not specified.')
        try:
            definition=query_parameters.getlist('definition')[0]
        except :
            print('Definition not specified.')
        server=None
        if word ==None:
            return Response('Some problem with the parameters pass with GET request')
        else:
            server=LookupWordViewSet.get_neo_server()
            LookupWordViewSet.start_neo('/home/snehal/data/examplesentencesgraph.db',server)
            graph=LookupWordViewSet.connect_to_neo()
        try:
            examples={}
            q=r"match (n {name:'"+word.replace("'","\\\'")+"'})-[r:sentence]->(m) with r.index as rindex limit 10 match ()-[r1:sentence {index:rindex}]->() with r1 as sentence , r1.index as r1index, r1.orderi as r1orderi order by r1.orderi desc  return collect(sentence),r1index "
            print q
            results=graph.cypher.execute(q)
            sentences=[]
            for result in results:
                relations=result[0]
                sentence=''
                for relation in relations:
                    sentence=relation.start_node.properties['name']+' '+sentence
                contexts=disambiguate(sentence)
                for context in contexts:
                    if context[0]==word:
                        synset=context[1]
                        if synset is not None:
                            definition=synset.definition()
                        else:
                            definition=[]
                sentences.append([definition,sentence+'.'])
            examples['word']=word
            examples['examples']=sentences            
        except:
            print(traceback.format_exc())
        return Response(examples)
            
