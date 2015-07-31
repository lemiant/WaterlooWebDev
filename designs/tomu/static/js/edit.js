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

function set_pending(target){
    if(!target.hasClass('pending')) {
        target.data('pending_start', new Date().getTime() )
        target.addClass('pending')
    }
}
function clear_pending(target){
    var now = new Date().getTime();
    setTimeout(function(){ target.removeClass('pending') }, 500 - (now - target.data('pending_start')))
}

var alter_pipelines = {}

function alter_context(target, value, timeout, callback){
	if(typeof timeout == 'undefined') timeout = 1000;
    var type = target.attr('class').split(' ')[0].slice(0,-7) // _widget
    var key = target.attr('id').slice(1) // _{{key}}
    
    set_pending(target)
	
	if(alter_pipelines[key]){
		if(typeof alter_pipelines[key] == "number")
			clearTimeout(alter_pipelines[key]);
		else if(typeof alter_pipelines[key] == "object")
			alter_pipelines[key].abort()
			alter_pipelines[key] = false
	}
	alter_pipelines[key] = setTimeout(function(){
		alter_pipelines[key] = $.ajax({
			url: '/alter',
			type: 'post',
			data: {
				type: "menu",
				key: key,
				value: JSON.stringify(value),
			}
		}).then(function(){
            clear_pending(target)
            alter_pipelines[key] = false
            if(callback) callback()
		})
	}, timeout)
}