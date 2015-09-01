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
import logging
logger = logging.getLogger(__name__)
class HelpViewSet(viewsets.ViewSet):
    
    @list_route(methods=['get'])
    def list_apis(self,request):
        logger.info( __name__)
        classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        apis=None
        logger.info( dir(sys.modules[__name__]))
        
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
            logger.info("Please specify both the words.")
            return False
        paths=[]
        if request.method=='GET':
            graph=LookupWordViewSet.connect_to_neo()
            if rels_to_use is not None :
                q=r"match (n {name:'"+start_word+"'}), (m {name:'"+end_word+"'}), p=allShortestPaths((n)-["+rels_to_use+"]->(m)) return relationships(p)"
            else:
                logger.info('Problem with the valdity of the input parameters. Please contact the programmer.')
            logger.info (q)
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
            logger.error(traceback.format_exc())    
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
                logger.info ('No relations specified')
            elif rels != 'all':
                construction=""
                for rel in rels_list:
                    construction=construction+":"+rel+'|'
                dict_of_details=(LookupWordViewSet.find_and_group_by_relation(word,construction[:-1]))
            else:
                dict_of_details=(LookupWordViewSet.find_and_group_by_relation(word,''))
            wordcard = WordCard(word=word,dictdetails=dict_of_details)
            logger.info (dict_of_details)
        else:
            logger.error('Http method not supported in this version.')
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
                logger.warn ('No relations specified')
            elif rels != 'all':
                construction=""
                for rel in rels_list:
                    construction=construction+":"+rel+'|'
                dict_of_details=(LookupWordViewSet.find_and_group_by_definition(word,construction[:-1]))
            else:
                dict_of_details=(LookupWordViewSet.find_and_group_by_definition(word,''))
                wordcard = WordCard(word=word,dictdetails=dict_of_details)
        else:
            logger.error('Http method not supported in this version.')
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
            if definition is None:
                continue
            if relationship_type not in edge_senses.keys():
                edge_senses[relationship_type]={}
            if definition not in edge_senses[relationship_type].keys():
                edge_senses[relationship_type][definition]={'words':[],'part_of_speech':''}                
            edge_senses[relationship_type][definition]['words'].append(node.properties['name'])
            edge_senses[relationship_type][definition]['part_of_speech']=relationship.properties['pos']
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
            if definition is None:
                continue            
            if definition not in edge_senses.keys():
                edge_senses[definition]={}
            if relationship_type not in edge_senses[definition].keys():
                edge_senses[definition][relationship_type]={'words':[],'part_of_speech':''}
            edge_senses[definition][relationship_type]['words'].append(node.properties['name'])
            edge_senses[definition][relationship_type]['part_of_speech']=relationship.properties['pos']           
        return edge_senses
    

#    @api_marker_decorator
#    @list_route(methods=['get'])
    def find_pos(self, request,arg1=None,arg2=None):
        word=arg1
        rels=arg2
        if request.method=='GET':
            rels_list=rels.split('_')
            if len(rels_list) ==0:
                logger.warn ('No relations specified')
            else:
                construction=""
                for rel in rels_list:
                    construction=construction+":"+rel+'|'
                dict_of_details=(LookupWordViewSet.find_and_group_by_relation(word,construction[:-1]))
                wordcard = WordCard(word=word,dictdetails=dict_of_details)
                logger.info (wordcard.dictdetails)
#                renderedjson = JSONRenderer().render(serializer.data)
            logger.info (dict_of_details)
        else:
            logger.error('Http method not supported in this version.')
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
        logger.info( query_parameters)
        word=query_parameters.getlist('word')[0]
        definition=None
        corpus_for_examples=None
        try:
            corpus_for_examples=query_parameters.getlist('corpus_to_use')[0]
        except :
            logger.error('Corpus_for_example not specified.')
        try:
            definition=query_parameters.getlist('definition')[0]
        except :
            logger.info('Definition not specified.')


        if word ==None:
            return Response('Some problem with the parameters pass with GET request')
        else:
            try:
                server=LookupWordViewSet.get_neo_server()
                LookupWordViewSet.start_neo('/home/snehal/data/graphwithoutexamples.db',server)     
                graph=LookupWordViewSet.connect_to_neo()
            except:
                return Response('Some problem with starting/restarting of the neo4j server.')                
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
            logger.error(traceback.format_exc())            
            logger.error('Http method not supported in this version.')
        return Response(examples)


    @staticmethod
    def get_neo_server():
        try:
            server = GraphServer(staticpaths.NEO4J_SERVER_DIST_PATH)
            return server
        except:
            logger.error(traceback.format_exc())    
            logger.error('Could not find and initialize the neo4j server')    
            return False


    @staticmethod
    def start_neo(db_dump_location='graph.db',server=None):
        logger.info (str(server.pid) + ' PIDDDDDDDDD ')
        if server.pid is None:
            try:
                server.update_server_properties(database_location=db_dump_location)
                server.start()
            except:
                logger.error('Some issue in server start.')
        else:
            logger.info('A server process is already running. Checking for the graph location in use....')
            if server.conf.get('neo4j-server','org.neo4j.server.database.location') !=db_dump_location:
                # set the name of the graph db dump location
                try:
                    server.stop()
                    server.update_server_properties(database_location=db_dump_location)
                    server.start()
                    logger.info('neo4j server has been successfully started.')
                except:
                    logger.error('Some issue in setting the db dump location. Defaulting to '+str(server.conf.get('neo4j-server','org.neo4j.server.database.location')))
                

    @staticmethod
    def stop_neo(server):
        try:
            server.stop()
        except:
            logger.error(traceback.format_exc())    
            logger.error('error in stoping')



    @staticmethod  
    def connect_to_neo():
        try:
            graph= Graph("http://"+settings.NEO4J_DATABASES['default']['USER']+":"+settings.NEO4J_DATABASES['default']['PASSWORD']+"@"+settings.NEO4J_DATABASES['default']['HOST']+":"+str(settings.NEO4J_DATABASES['default']['PORT'])+settings.NEO4J_DATABASES['default']['ENDPOINT'])
            return graph
        except:
            logger.error(traceback.format_exc())    
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
            logger.error('Corpus_for_example not specified.')
        try:
            definition=query_parameters.getlist('definition')[0]
        except :
            logger.error('Definition not specified.')
        server=None
        if word ==None:
            return Response('Some problem with the parameters pass with GET request')
        else:
            server=LookupWordViewSet.get_neo_server()
            LookupWordViewSet.start_neo('/home/snehal/data/examplesentencesgraph.db',server)
            graph=LookupWordViewSet.connect_to_neo()
        try:
            examples={}
            q=r"match (n {name:'"+word.replace("'","\\\'")+"'})-[r:sentence]->(m) with r.index as rindex limit 1 match ()-[r1:sentence {index:rindex}]->() with r1 as sentence , r1.index as r1index, r1.orderi as r1orderi order by r1.orderi desc  return collect(sentence),r1index "
            logger.info( q)
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
            logger.error(traceback.format_exc())
        return Response(examples)
            
