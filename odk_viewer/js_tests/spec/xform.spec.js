describe("Formhub Form", function () {
    var form_url = "/larryweya/forms/tutorial/form.json";
    var form;

    beforeEach(function(){
        var loaded;
        var result = {
            id_string: "tutorial",
            default_language: "default",
            type: "survey",
            name: "tutorial",
            sms_keyword: "tutorial",
            title: "Tutorial Form",
            children: [
                {
                    name: "start_time",
                    type: "start"
                },
                {
                    name: "end_time",
                    type: "end"
                },
                {
                    name: "instruction_note",
                    label: "Make sure you fill out the questionnaire accurately.",
                    type: "note"
                },
                {
                    name: "location",
                    hint: "So you can find it again",
                    label: "Location",
                    type: "gps"
                },
                {
                    name: "nearest_watering_hole",
                    hint: "Where is the nearest watering hole",
                    label: "Watering Hole",
                    type: "geopoint"
                },
                {
                    name: "a_group",
                    label: "A Group",
                    type: "group",
                    children: [
                        {
                            name: "how_epic",
                            label: "On a scale of 1-10, how epic an eat",
                            type: "integer"
                        },
                        {
                            name: "how_delectible",
                            label: "On a scale of 1-10, how delectible",
                            type: "integer"
                        },
                        {
                            name: "a_nested_group",
                            type: "group",
                            label: "A Nested Group",
                            children: [
                                {
                                    name: "nested_q",
                                    type: "text",
                                    label: "A Nested Q"
                                }
                            ]
                        }
                    ]
                },
                {
                    name: "rating",
                    label: "Rating",
                    type: "select one",
                    children: [
                        {
                            name: "nasty",
                            label: "Epic Eat"
                        },
                        {
                            name: "delectible",
                            label: "Delectible"
                        },
                        {
                            name: "nothing_special",
                            label: "Nothing Special"
                        },
                        {
                            name: "bad",
                            label: "What was I thinking"
                        }
                    ]
                }
            ]
        };

        form = new FHForm({}, {url: form_url});
        spyOn(form, 'fetch').andCallThrough();
        spyOn(Backbone, 'ajax').andCallFake(function(params, options){
            var deferred = $.Deferred();
            deferred.done(function(response){
                params.success(response);
            });
            deferred.resolve(result, 'success', deferred);
            return deferred.promise();
        });

        runs(function(){
            loaded = false;
            form.on('load', function(){
                loaded = true;
            });
            form.init();
        });

        waitsFor(function(){
            return loaded;
        }, "Waiting for form to load", 1000);
    });

    it("loads on init", function(){
        expect(Backbone.ajax).toHaveBeenCalled();
        expect(form.fetch).toHaveBeenCalled();
    });

    describe("Parse Questions", function(){
        var parsed, raw_questions;

        beforeEach(function(){
            raw_questions = form.get(FHForm.constants.CHILDREN);
            parsed = FHForm.parseQuestions(raw_questions);
            expect(parsed).toBeDefined();
            expect(parsed.length).toEqual(8);
        });

        it("can parse nested questions into a single level", function(){
            // get field names
            var field_names = parsed.map(function(q){
                return q.name;
            });
            expect(field_names).toContain('start_time');
            expect(field_names).toContain('end_time');
            expect(field_names).not.toContain('instruction_note');
            expect(field_names).toContain('location');
            expect(field_names).toContain('nearest_watering_hole');
            expect(field_names).toContain('rating');
            expect(field_names).not.toContain('a_group');
            expect(field_names).toContain('how_epic');
            expect(field_names).toContain('how_delectible');
        });

        it("sets id from fields name for top level children", function(){
            var nearest_watering_hole = _.find(parsed, function (q) {
                return q.name === 'nearest_watering_hole';
            });
            expect(nearest_watering_hole).toBeDefined();
            expect(nearest_watering_hole.xpath).toEqual(nearest_watering_hole.name)
        });

        it("sets id from fields parent's name and name for nested children", function(){
            var how_epic = _.find(parsed, function (q) {
                return q.name === 'how_epic';
            });
            expect(how_epic).toBeDefined();
            expect(how_epic.xpath).toEqual(['a_group', how_epic.name].join('/'));

            var how_delectible = _.find(parsed, function (q) {
                return q.name === 'how_delectible';
            });
            expect(how_delectible).toBeDefined();
            expect(how_delectible.xpath).toEqual(['a_group', how_delectible.name].join('/'));

            var nested_q = _.find(parsed, function (q) {
                return q.name === 'nested_q';
            });
            expect(nested_q).toBeDefined();
            expect(nested_q.xpath).toEqual(['a_group', 'a_nested_group', nested_q.name].join('/'));
        });
    });

    describe("Questions By Type", function(){
        it("can return questions by type", function () {
            var gps_questions = form.questionsByType(FHForm.types.GEOLOCATION);
            expect(gps_questions.length).toEqual(2);

            var question_names = _.map(gps_questions, function(q){
                return q.get('name');
            });
            expect(question_names).toContain('location');
            expect(question_names).toContain('nearest_watering_hole');
        });
    });
});