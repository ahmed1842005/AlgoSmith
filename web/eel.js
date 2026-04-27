var eel = new function() {
    function hosts() {
        var scripts = document.getElementsByTagName('script');
        for (var i = 0; i < scripts.length; i++) {
            if (scripts[i].src && scripts[i].src.indexOf('eel.js') !== -1) {
                var parts = scripts[i].src.split('/');
                parts.pop();
                return parts.join('/');
            }
        }
        return '';
    }
    
    var host = hosts();
    var exposed_functions = {};
    var call_queue = [];
    
    this.expose = function(f, name) {
        exposed_functions[name] = f;
    };
    
    function call(name, args) {
        var js = '(exposed_functions["' + name + '"])(' + JSON.stringify(args) + ')';
        return eval(js);
    }
    
    this.call = function(name, args, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', host + '/call');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function() {
            if (callback) {
                var result = JSON.parse(xhr.responseText);
                callback(result);
            }
        };
        xhr.send(JSON.stringify({name: name, args: args}));
    };
};

if (typeof window.eel === 'undefined') {
    window.eel = eel;
}