Question = function(questionData)
{
    this.name = questionData.name;
    this.type = questionData.type;
    this.label = questionData.label;
}

Question.prototype.getLabel = function(language)
{
    /// if plain string, return
    if(typeof(this.label) == "string")
        return this.label;
    else if(typeof(this.label) == "object")
    {
        if(language && this.label.hasOwnProperty(language))
            return this.label[language];
        else
        {
            var label = null;
            for(key in this.label)
            {
                label = this.label[key];
                break;// break at first instance and return that
            }
            return label;
        }

    }
    // return raw name
    return this.name;
}

function parseQuestions(children, prefix, cleanReplacement)
{
    var idx;
    cleanReplacement = typeof cleanReplacement !== 'undefined' ? cleanReplacement : '_';

    for(idx in children)
    {
        var question = children[idx];
        //@TODO: do we just want to add anything with children, concern could be it item has children and is alos avalid question - if thats possible
        if(question.hasOwnProperty('children') && (question.type == "group" || question.type == "note" || question.type == "repeat"))
        {
            parseQuestions(question.children, ((prefix?prefix:'') + question.name + cleanReplacement));
        }
        else
        {
            // TODO: question class that has accessor mesthods for type, label, language etc
            questions[((prefix?prefix:'') + question.name)] = new Question(question);
        }
    }
}