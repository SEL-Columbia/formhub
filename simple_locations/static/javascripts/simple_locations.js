      //make sure map is a global variable
      var map;

      function refresh_tree() {
        $('#tree').load('/simple_locations/render_tree/');
      }
      
      function load_add_location() {
        $('#edit_location').load('/simple_locations/add/');      
      }
      
      function load_add_location_child(location_id) {
        $('#edit_location').load('/simple_locations/add/' + location_id + '/');
      }
      
      function load_edit_location(location_id) {
        $('#edit_location').load('/simple_locations/edit/' + location_id + '/');
      }
      
      function add_location(link) {
          form = $(link).parents("form");
          form_data = form.serializeArray();
          $('#edit_location').load(form.attr("action"), form_data, function() { refresh_tree() });      
      }
      
      function save_location(link) {
          form = $(link).parents("form");
          form_data = form.serializeArray();
          $('#edit_location').load(form.attr("action"), form_data, function() { refresh_tree() });
      }
      
      function delete_location(location_id) {
    	  if (confirm("Are you sure?")) {
        $.ajax({'async':false,
              'cache':false,
              'type':'POST',
              'url':'/simple_locations/delete/' + location_id + '/',
              'success': function() { refresh_tree(); load_add_location(); }  
             });
    	  } else {
    		  return false;
    		  
    	  }
      }
      
      $(document).ready(function() {
        refresh_tree();
        load_add_location();   
       
      });