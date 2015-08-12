# This is the words module that handles all of the details about the word
import models
word_attributes={'synonym':'synonym',
            'antonym':'antonym',
            'hypernym':'hypernym',
            'hyponym':'hyponym',
            'entailment':'entailment',
            'derivation':'dform',
            'pholonym':'pholonym',
            'pmeronym':'pmeronym',
            'sholonym':'sholonym',
            'smeronym':'smeronym',
            'definition':'definition',
            }

def GetDetails(word,details_to_look_for,groupbysenses):
    details={}
    print (groupbysenses)
    for detail in details_to_look_for:
        relation =word_attributes[detail]
        if groupbysenses is not False:
            words=models.lookup_rel_sense(word,relation)
            if words is not False:
                details[detail]=words
            print str(words) + '  >>>>>>>>  '+detail
                
        else:
            words=models.lookup_based_on_rel(word,relation)
            if words is not False:
                details[detail]=words
            print str(words) + '  >>>>>>>>  '+detail
    return details
    


