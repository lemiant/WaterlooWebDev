window.fallback = {
    exists: function(identifiers){
        if(typeof identifiers == 'string') identifiers = [identifiers]
        for(var n=0; n<identifiers.length; n++){
            //console.log(identifiers)
            var parts = identifiers[n].split('.')
            node = window
            for(var i=0; i<parts.length; i++){
                node = node[parts[i]]
                if(typeof node == 'undefined') return false
            }
        }
        return true
    },
    fallback_script: function(identifiers, backup){
        if(!fallback.exists(identifiers)) document.write('<script type="text/javascript" src="'+backup+'"></'+'script>');
    },
    blocked_callback: function(identifiers, callback, refresh_rate){
        if(!refresh_rate) var refresh_rate = 50;
        return function(){
            if(fallback.exists(identifiers)) callback.apply(this, arguments)
            else{
                var t = this
                var args = arguments
                setTimeout(function(){ blocked_callback(identifiers, callback).apply(t, args) }, refresh_rate)
            }
        }
    }
}