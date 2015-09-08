from django.db import models as snippetmodels
from jsonfield import JSONField

# A word-card model is created. The primary use of this model is to store recently lookedup words and their relationships in this graphlet. We use the term graphlet to define a subgraph. For this purpose we use networkx python package to store the retrieved graph. 


class WordCard(snippetmodels.Model):
    word=snippetmodels.CharField(max_length=100)
    dictdetails=snippetmodels.CharField(max_length=100)
#    meanings=snippetmodels.CharField(max_length=500)
#    synonyms=snippetmodels.CharField(max_length=500)
#    antonyms=snippetmodels.CharField(max_length=500)
#    entailments=snippetmodels.CharField(max_length=500)
#    derivations=snippetmodels.CharField(max_length=500)
#    hyponyms=snippetmodels.CharField(max_length=500)
#    hypernyms=snippetmodels.CharField(max_length=500)
