xig = {
	"init": function() {
		var sys;
		for (sys in xig) {
			if (xig[sys].init != undefined) {
				xig[sys].init();
			}
		}
	},
	"poll": function() {
		dojo.xhrGet( {
            url: "/poll",
            handleAs: "json",
            load: xig.handler,
            error: xig.error
        });		
	},
	"handler": function(data) {
		var sys;
		for (sys in data){
			if (xig[sys].handler != undefined){
				xig[sys].handler(data[sys]);	
			} else {
				alert("Missing handler for: "+sys);
			}
			
		}
	},
	"error": function(status) {
		var sys;
		for (sys in xig){
			if (xig[sys].error != undefined){
				xig[sys].error(status);
			}
		}
		//alert("Poll error: "+status);
	},
	"power": {
		"state": "", // on or off
		"init": function() {
			xig.power.set_button_state("disabled");
			xig.power.get_state();
		},
		"toggle": function(apply) { // turn on/off the power, whether to send the command to the server as well.
			// send message to server to turn on power
			if (xig.power.state == "off") {
				xig.power.set("on");
			} else {
				xig.power.set("off");
			}
		},
		"set": function(state) { // turn on power
			// disable the button
			xig.power.set_button_state("disabled");
			dojo.xhrPost({
	            url: "/xig",
	            content: {"power": state},
	            handleAs: "json",
	            //load: xig.power.set_button_state,
	            error: xig.power.get_state
			});
		},
		"set_button_state": function(state) { // enable the power button 
			var power_button = dojo.byId('power_button');
			power_button.className="power_icon "+state;
			if (state == "disabled") {
				power_button.disabled=true;
			} else {
				xig.power.state = state;
				power_button.disabled=false;
			}
		},
		"get_state": function() {
			dojo.xhrGet( {
	            url: "/xig",
	            handleAs: "json",
	            load: xig.power.set_button_state	            
	        });			
		},
		"handler": function(state) {xig.power.set_button_state(state);}
	},
	"settings": {
		"callbacks": {}, // key, callback
		"get": function(oArg) { // key, on_load, on_error, notify=true/false
	        var content = {'key': oArg.key};
	        if (oArg.notify){
	        	content.notify = oArg.notify;
	        	xig.settings.callbacks[oArg.key] = oArg.on_load;
	        }
			if (oArg.on_load) {
				dojo.xhrGet( {
		            url: "/settings",
		            content: content,
		            handleAs: "json",
		            load: oArg.on_load,
		            error: oArg.on_error		            
		        });
	        } else {
	        	var return_val;
				dojo.xhrGet( {
		            url: "/settings",
		            content: content,
		            handleAs: "json",
		            sync: true,
		            load: function(value) {return_val = value;},
		            error: function() {return_val = "";}
		        });
				while(return_val == undefined);
				return return_val;
	        }
		},
		"set": function(oArg) { // key, value, on_load, on_error
			dojo.xhrPost( {
	            url: "/settings",
	            content: {'key': oArg.key, 'value': oArg.value},
	            handleAs: "json",
	            load: oArg.on_load,
	            error: oArg.on_error            
	        });
		},
		"handler": function(data) {
			var key;
			for (key in data) {
				if (xig.settings.callbacks.key) {
					xig.settings.callbacks.key(data);
				}
			}
		}
	},
	"xbee": {
		"get": function(oArg) { // addr, at, on_load, on_error
	        if (oArg.on_load) {
				dojo.xhrGet( {
		            url: "/xbee",
		            content: {'at': oArg.at, 'addr': oArg.addr},
		            handleAs: "json",
		            load: oArg.on_load,
		            error: oArg.on_error		            
		        });
	        } else {
	        	var return_val;
				dojo.xhrGet( {
		            url: "/xbee",
		            content: {'at': oArg.at, 'addr': oArg.addr},
		            handleAs: "json",
		            sync: true,
		            load: function(value) {return_val = value;},
		            error: function() {return_val = "";}
		        });
				while(return_val == undefined);
				return return_val;
	        }
		},
		"set": function(oArg) { //addr, at, value, on_load, on_error
			dojo.xhrPost( {
	            url: "/xbee",
	            content: {'at': oArg.at, 'addr': oArg.addr, 'value': oArg.value},
	            handleAs: "json",
	            load: oArg.on_load,
	            error: oArg.on_error            
	        });
		}
	},
	"idigi": {
		"init": function() {xig.idigi.update();},
		"update": function() {
	        dojo.xhrGet( {
	            url: "/idigi",
	            handleAs: "json",
	            load: xig.idigi.handler
	        });    	
		},
		"handler": function(value) {
			dojo.byId('idigi-status').innerHTML=value;
	    }
	},
	"serial_ports": {
		"init": function() {xig.serial_ports.update();},
		"update": function() {
            dojo.xhrGet( {
                url: "/serial_ports",
                handleAs: "json",
                sync: true,
                load: xig.serial_ports.handler,
            	error: function() {setTimeout("xig.serial_ports.update()", 2000);} //try again after two seconds on error
            });		
		},
		"handler": function(com_ports){
        	var i;
        	var com_port_select = dojo.byId('xbee-com_port');
        	// TODO: do a merge of COM Ports
        	for (i in com_ports) {
        	    var option=document.createElement("option");
        	    option.text=com_ports[i];
        		com_port_select.add(option, null);			
        	}
		}
	},
	"logs": {
		"store": null,
		"id": 0,
		"init": function() { 
			xig.logs.store = new dojo.data.ItemFileWriteStore({data: {identifier: 'id', label: 'created', items: []}});},
		"update": function() {
	        dojo.xhrGet( {
	            url: "/logs",
	            handleAs: "json",
	            load: xig.logs.handler
	        });
		},
		"handler": function(record_list){
        	var r;
        	for (r in record_list) {
        		var record = record_list[r];
        		record.id = xig.logs.id;
        		xig.logs.id = xig.logs.id + 1;
        		xig.logs.store.newItem(record);
        	}
        	xig.logs.store.save();			
		}
	}
};