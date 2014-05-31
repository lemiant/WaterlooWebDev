$('.text_edit')
    .css('background-color', '#dff6e2')
    .css('padding', '3px')
    .on('input', text_input)

last_inputs = {}
function text_input(){
    var t = $(this),
        type = ((t.is('textarea')) ? 'textarea' : 'input'),
        key = t.attr('id').slice(0,-7),
        value = t.val()
    
    t.css('background-color', '#ffffc0')
    
    if(last_inputs[key]){
        if(typeof last_inputs[key] == "number")
            clearTimeout(last_inputs[key]);
        else if(typeof last_inputs[key] == "object")
            last_inputs[key].abort()
    }
    last_inputs[key] = setTimeout(function(){
        console.log(value)
        last_inputs[key] = $.ajax({
            url: '/alter',
            type: 'post',
            data: {
                    type: type,
                    key: key,
                    value: value
                }
        }).then(function(resp){
            t.css('background-color', '#dff6e2')
            last_inputs[key] = false;
        }, function(){ last_inputs[key] = false;  })
    }, 500)
}


$('.map_edit')
    .css('background-color', '#dff6e2')
    .css('padding', '3px')
    .on('input', map_input)
function map_input(){
    var t = $(this),
        key = t.attr('name'),
        value = t.val()
    
    t.css('background-color', '#ffffc0')
    
    if(last_inputs[key]){
        if(typeof last_inputs[key] == "number")
            clearTimeout(last_inputs[key]);
        else if(typeof last_inputs[key] == "object")
            last_inputs[key].abort()
    }
    last_inputs[key] = setTimeout(function(){
        console.log(value)
        last_inputs[key] = $.ajax({
            url: '/alter',
            type: 'post',
            data: {
                    type: "map",
                    key: key,
                    value: value
                }
        }).then(function(resp){
            t.css('background-color', '#dff6e2')
            $('#'+key+'_widget').after(resp).remove()
            last_inputs[key] = false;
        }, function(){ last_inputs[key] = false;  })
    }, 500)
}


$('.img_form')
    .on('change', change_img)

function change_img(){
    var key = $(this.key).val(),
        t = $('#'+key+'_widget'),
        formData = new FormData($(this)[0]);
 
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