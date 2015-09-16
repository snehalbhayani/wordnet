from django.utils.datastructures import MultiValueDictKeyError
from py2neo import Node, Relationship, Graph, neo4j
from py2neo.server import GraphServer
from django.db import models
from rest_framework import status
from rest_framework.decorators import list_route
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.conf import settings
import traceback
import sys,inspect
import logging
from elasticsearch import Elasticsearch
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

class SearchViewSet(viewsets.ViewSet):

    @api_marker_decorator
    @list_route(methods=['get'])
    def items(self,request):
        """
        ENDPOINT:/v1/search/
        PARAMETERS:1.  <terms> is a comma-separated list of terms to be used for searching.
                   2.  <page> specifies the page in the result set to be extracted.
                   3.  <size> is the size of the page 

        """
        success='Failure'
        try:
            terms_list=str(request.GET['terms']).split(',')
        except:
            logger.error(traceback.format_exc())
            return Response({'status':success,'message':'Some error in query terms that were specified.'})
        try:
            result_page=int(request.GET['page'])
            result_size=int(request.GET['size'])
        except ValueError:
            logger.error(traceback.format_exc())
            return Response({'status':success,'message':'Please provide integer values for page and size parameters.'})
        except MultiValueDictKeyError:
            print(traceback.format_exc())
            return Response({'status':success,'message':'Please provide values for size and page. '})
                
            
        query_body={"query":{"query_string":{"fields": ["item_title","item_description","item_author_name","item_tags"], "query":"*"+terms_list[0].strip()+"*"}}}
        results=self.search_index('item',query_body,'learnapt',result_size,result_page)    
        if len(results)>0:
            success='Success'
        return Response({'status':success,'results':results})

    @api_marker_decorator
    @list_route(methods=['get'])
    def lessons(self,request):
        """
        ENDPOINT:/v1/search/
        PARAMETERS:1.  <terms> is a comma-separated list of terms to be used for searching.
                   2.  <page> specifies the page in the result set to be extracted.
                   3.  <size> is the size of the page 

        """
        success='Failure'
        try:
            terms_list=str(request.GET['terms']).split(',')
        except:
            logger.error(traceback.format_exc())
            return Response({'status':success,'message':'Some error in query terms that were specified.'})
        try:
            result_page=int(request.GET['page'])
            result_size=int(request.GET['size'])
        except ValueError:
            logger.error(traceback.format_exc())
            return Response({'status':success,'message':'Please provide integer values for page and size parameters.'})
        except MultiValueDictKeyError:
            print(traceback.format_exc())
            return Response({'status':success,'message':'Please provide values for size and page. '})    
      
        query_body={"query":{"query_string":{"fields": ["lesson_name","lesson_owner_name","lesson_slug","lesson_sub_title", "lesson_collaborators","lesson_tags"], "query":"*"+terms_list[0].strip()+"*"}} }
        results=self.search_index('lesson',query_body,'learnapt',result_size,result_page)    
        if len(results)>0:
            success='Success'
        return Response({'status':success,'results':results})

    @api_marker_decorator
    @list_route(methods=['get'])
    def users(self,request):
        """
        ENDPOINT:/v1/search/
        PARAMETERS:1.  <terms> is a comma-separated list of terms to be used for searching.
                   2.  <fields> specifies the fields to be used for searching.
                   3.  <op> is a comma separated list of operators to be used for building the search query.

        """
        success='Failure'
        try:
            terms_list=str(request.GET['terms']).split(',')
        except:
            logger.error(traceback.format_exc())
            return Response({'status':success,'message':'Some error in query terms that were specified.'})
        try:
            result_page=int(request.GET['page'])
            result_size=int(request.GET['size'])
        except ValueError:
            logger.error(traceback.format_exc())
            return Response({'status':success,'message':'Please provide integer values for page and size parameters.'})
        except MultiValueDictKeyError:
            print(traceback.format_exc())
            return Response({'status':success,'message':'Please provide values for size and page. '})
        
        query_body={"query":{"query_string":{"fields": ["user_name","user_fullname","user_email","user_id"], "query":"*"+terms_list[0].strip()+"*"}} }
        results=self.search_index('user',query_body,'learnapt',result_size,result_page)    
        if len(results)>0:
            success='Success'
        return Response({'status':success,'results':results})

    @api_marker_decorator
    @list_route(methods=['get'])
    def organizations(self,request):
        """
        ENDPOINT:/v1/search/
        PARAMETERS:1.  <terms> is a comma-separated list of terms to be used for searching.
                   2.  <fields> specifies the fields to be used for searching.
                   3.  <op> is a comma separated list of operators to be used for building the search query.

        """
        try:
            terms_list=str(request.GET['terms']).split(',')
            fields_list=str(request.GET['fields']).split(',')
        except:
            logger.error(traceback.format_exc())
        response=es.search(index='_all', body={"query":{"query_string":{"fields": [""], "query":"*"+terms_list[0].strip()+"*"}} })
        return Response(response)
        
    def search_index(self,search_from,query_body,index_name,result_size,result_page):
        try:
            es=Elasticsearch()        
        except:
            logger.error(traceback.format_exc())
            return []
        search_response=es.search(index=index_name, body=query_body, scroll='100000m',size=result_size,doc_type=search_from)
        if result_page is 1:
            results=list(search_response['hits']['hits'])
        else:
            results=[]
        scrollid=search_response['_scroll_id']
        while(len(search_response['hits']['hits'])>0 and result_page>1):
            result_page =result_page-1
            search_response=es.scroll(scroll_id=scrollid,scroll='1000m')
            if result_page is 1:
                results=search_response['hits']['hits']        
        return results
