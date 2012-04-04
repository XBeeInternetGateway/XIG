xig = {
	"init": function() {
		xig.power.init();
		xig.logs.init();
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
	            load: xig.power.set_button_state,
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
		}
	},
	"settings": {
		"get": function(oArg) { // key, on_load, on_error
	        if (oArg.on_load) {
				dojo.xhrGet( {
		            url: "/settings",
		            content: {'key': oArg.key},
		            handleAs: "json",
		            load: oArg.on_load,
		            error: oArg.on_error		            
		        });
	        } else {
	        	var return_val;
				dojo.xhrGet( {
		            url: "/settings",
		            content: {'key': oArg.key},
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
	"logs": {
		"store": null,
		"id": 0,
		"init": function() { xig.logs.store = new dojo.data.ItemFileWriteStore({data: {identifier: 'id', label: 'created', items: []}});},
		"update": function() {
	        dojo.xhrGet( {
	            url: "/logs",
	            handleAs: "json",
	            load: function(record_list) {
	            	var r;
	            	for (r in record_list) {
	            		var record = record_list[r];
	            		record.id = xig.logs.id;
	            		xig.logs.id = xig.logs.id + 1;
	            		xig.logs.store.newItem(record);
	            	}
	            	xig.logs.store.save();
	            }
	        });
		}
	}
};