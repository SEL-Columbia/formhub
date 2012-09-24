var SurveyData =
{
    name: 'survey',
    type: 'survey',
    label: 'A Survey',
    children: [
        {
            name: 'note_one',
            type: 'group',
            label: 'A Note',
            children: [
                {
                    name: 'a_group',
                    type: 'group',
                    label: 'Another Group',
                    children: [
                        {
                            name: 'a_question',
                            type: 'text',
                            label: 'A Question'

                        }
                    ]
                }
            ]
        }
    ]
};
var questions = {};