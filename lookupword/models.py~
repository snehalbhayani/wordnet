from py2neo import Node, Relationship, Graph, neo4j
from django.db import models
from neo4django.db import models as gmodels




# Create your models here.


class WordNode(gmodels.NodeModel):
    name = gmodels.StringProperty(indexed=True)
    synonym = gmodels.Relationship('self',rel_type='synonym')


class Word(models.Model):
    word=models.CharField(max_length=100)

class Sense(models.Model):
    sense=models.CharField(max_length=100)

class Synonym(models.Model):
    word=models.ForeignKey(Word)
    sense=models.ForeignKey(Sense)    


class Antonym(models.Model):
    word=models.ForeignKey(Word)
    sense=models.ForeignKey(Sense)    


class Hyponym(models.Model):
    word=models.ForeignKey(Word)
    sense=models.ForeignKey(Sense)    


class Hypernym(models.Model):
    word=models.ForeignKey(Word)
    sense=models.ForeignKey(Sense)    


class Entailment(models.Model):
    word=models.ForeignKey(Word)
    sense=models.ForeignKey(Sense)    

def GetTheWordDetails(word):
    graph=connect_to_neo()
    #graph_db = neo4j.GraphDatabaseService()
    details=graph.find('word',property_key='name', property_value=word)
    for detail in details:
        print(detail)
    #details=WordNode.objects.get(name=word)
    return details

def lookup_based_on_rel(word,relation):
    graph=connect_to_neo()
    #graph_db = neo4j.GraphDatabaseService()
    node=graph.find_one('word',property_key='name', property_value=word)
    relations=list(graph.match(start_node=node, rel_type=relation))
    if len(relations)>0:
        nodes_based_on_relation=[]
        
        for rel in relations:
            print(rel.properties['definition'])
            nodes_based_on_relation.append(rel.end_node.properties['name'])
        return list(set(nodes_based_on_relation))
    else:
        return False

def lookup_rel_sense(word,relation):
    graph=connect_to_neo()
    #graph_db = neo4j.GraphDatabaseService()
    node=graph.find_one('word',property_key='name', property_value=word)
    relations=list(graph.match(start_node=node, rel_type=relation))
    if len(relations)>0:
        nodes_based_on_relation=[]
        
        for rel in relations:
            print(rel.properties['definition'])
            nodes_based_on_relation.append(rel.end_node.properties['name'])
        return list(set(nodes_based_on_relation))
    else:
        return False


def connect_to_neo():
    try:
        graph= Graph("http://neo4j:441989@localhost:7474/db/data/")
        return graph
    except:
        print(traceback.format_exc())    
        return False
    

