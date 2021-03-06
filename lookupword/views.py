from django.shortcuts import render
from forms import WordForm
import words
def WordView(request):
    template_name = 'form_for_word.html'
    form = WordForm()
    return render(request, template_name, {'form': form})
    
    




def LookupWord(request):
    template_name = 'form_for_details.html'
    form = WordForm()
    query_dict=request.POST    
    word_to_lookup=query_dict['word']
    if 'groupbysenses' in query_dict:
        group_by_senses=query_dict['groupbysenses']
    else :
        group_by_senses=False
        
    rel_to_look=query_dict.getlist('choices')
    details=words.GetDetails(word_to_lookup,rel_to_look,group_by_senses)
    return render(request, template_name, {'form': form,'details':details,'word':word_to_lookup})
    


