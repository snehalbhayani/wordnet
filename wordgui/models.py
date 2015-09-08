from django.db import models

class User(models.Model):
    user_name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    class Admin: pass    

class Search(models.Model):
    search_type = models.CharField(max_length=100)
    words = models.CharField(max_length=100)
    class Admin: pass  
    
    
