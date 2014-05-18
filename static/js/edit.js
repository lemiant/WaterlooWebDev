$('.text_edit')
    .css('background-color', '#dff6e2')
    .css('padding', '3px')
    .on('input', text_input)

last_inputs = {}
function text_input(){
    var t = $(this),
        widget = t.attr('id'),
        value = t.val()
    
    t.css('background-color', '#ffffc0')
    
    if(last_inputs[widget]){
        if(typeof last_inputs[widget] == "number")
            clearTimeout(last_inputs[widget]);
        else if(typeof last_inputs[widget] == "object")
            last_inputs[widget].abort()
    }
    last_inputs[widget] = setTimeout(function(){
        console.log(value)
        last_inputs[widget] = $.ajax({
            url: '/alter',
            type: 'post',
            data: {
                    widget: widget,
                    value: value
                }
        }).then(function(resp){
            t.css('background-color', '#dff6e2')
            if(t.hasClass('map_input'))
                $('#'+widget+'_map').after(resp).remove()
            last_inputs[widget] = false;
        }, function(){ last_inputs[widget] = false;  })
    }, 500)
}


$('.img_form')
    .on('change', change_img)

function change_img(){
    widget = $(this.widget).val()
    t = $('#'+widget)
    console.log($(this)[0])
    var formData = new FormData($(this)[0]);
    console.log(formData)
 
  $.ajax({
    url: '/alter',
    type: 'POST',
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function (resp) {
      t.attr('src', resp)
    }
  });
}