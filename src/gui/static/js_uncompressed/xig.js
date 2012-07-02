xig = {
	"init": function() {
		var sys;
		for (sys in xig) {
			if (typeof xig[sys].init != "undefined") {
				xig[sys].init();
			}
		}
	},
	"poll": {
		"connected": false,
		"init": function() {
			xig.poll.send(true);
			setInterval('xig.poll.send();', 1000);
		},
		"send": function(refresh) {
			dojo.xhrGet( {
	            url: "/poll",
	            handleAs: "json",
	            content: {refresh:refresh},
	            load: xig.poll.handler,
	            error: xig.poll.error,
	            preventCache: true
	            //timeout: 1000,
	        });		
		},
		"handler": function(data) {
			if (xig.poll.connected == false) {
				xig.poll.connected = true;
				// switched from disconnected to connected
				xig.logs.add({msg: "Connected to XIG server", levelname: "INFO"});
			}
			var sys;
			var some_response = false;
			for (sys in data){
				some_response = true;
				if (typeof xig[sys].handler != "undefined"){
					try {
						xig[sys].handler(data[sys]);
					} catch(err) {
						xig.logs.add({msg: "Error when handling poll response: "+err.toString(), levelname: "WARNING"});
					}
				} else {
					xig.logs.add({msg: "Missing handler for: "+sys});
				}
			}
		},
		"error": function(status) {
			// report the errors
			xig.logs.add({msg: "Poll error: "+status});
		},
	},
	"power": {
		"state": "", // on or off
		"init": function() {
			xig.power.set_button_state("disabled");
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
	            error: xig.power.get_state,
	            preventCache: true
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
	            load: xig.power.set_button_state,
	            preventCache: true
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
		            error: oArg.on_error,
		            preventCache: true
		        });
	        } else {
	        	var return_val;
				dojo.xhrGet( {
		            url: "/settings",
		            content: content,
		            handleAs: "json",
		            sync: true,
		            load: function(value) {return_val = value;},
		            error: function() {return_val = "";},
		            preventCache: true
		        });
				while(typeof return_val == "undefined");
				return return_val;
	        }
		},
		"set": function(oArg) { // key, value, on_load, on_error
			dojo.xhrPost( {
	            url: "/settings",
	            content: {'key': oArg.key, 'value': oArg.value},
	            handleAs: "json",
	            load: oArg.on_load,
	            error: oArg.on_error,
	            preventCache: true
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
		            error: oArg.on_error,
		            preventCache: true
		        });
	        } else {
	        	var return_val;
				dojo.xhrGet( {
		            url: "/xbee",
		            content: {'at': oArg.at, 'addr': oArg.addr},
		            handleAs: "json",
		            sync: true,
		            load: function(value) {return_val = value;},
		            error: function() {return_val = "";},
		            preventCache: true
		        });
				while(typeof return_val == "undefined");
				return return_val;
	        }
		},
		"set": function(oArg) { //addr, at, value, on_load, on_error
			dojo.xhrPost( {
	            url: "/xbee",
	            content: {'at': oArg.at, 'addr': oArg.addr, 'value': oArg.value},
	            handleAs: "json",
	            load: oArg.on_load,
	            error: oArg.on_error,
	            preventCache: true
	        });
		},
		"handler": function(values) {
			var key;
			for (key in values) {
				var value = values[key];
				if (key == "status") {
		        	dojo.byId('xbee-status').innerHTML=value;
		        	var status_div = dojo.byId('xbee-status-param');
		            if (value == "Joined or Formed Network") {
		            	status_div.className = "parameter success"; 
		            } else {
		            	status_div.className = "parameter error";
		            }        						
				} else if (key == "eui") {
					dojo.byId('xbee-eui').innerHTML=value;
				}
			}
		}
	},
	"idigi": {
		"update": function() {
	        dojo.xhrGet( {
	            url: "/idigi",
	            handleAs: "json",
	            load: xig.idigi.handler,
	            preventCache: true
	        });    	
		},
		"handler": function(value) {
        	dojo.byId('idigi-status').innerHTML=value;
        	var status_div = dojo.byId('idigi-status-param');
            if (value == "Connected") {
            	status_div.className = "parameter success"; 
            } else {
            	status_div.className = "parameter error";
            }        	
	    }
	},
	"serial_ports": {
		"update": function() {
            dojo.xhrGet( {
                url: "/serial_ports",
                handleAs: "json",
                sync: true,
                load: xig.serial_ports.handler,
            	error: function() {setTimeout("xig.serial_ports.update()", 2000);}, //try again after two seconds on error
            	preventCache: true
            });		
		},
		"handler": function(new_list){
        	var i;
        	var com_port_select = dojo.byId('xbee-com_port');
        	var select_index = 0;
        	var new_index = 0;
        	new_list.unshift(''); // add an empty element to COM port list (for initial startup and to clear COM settings).
        	while (1) {
        		// merge the new items into the select options
        		// this relies on both lists being ordered
        		if(select_index >= com_port_select.options.length) {
        			// no more items in select, add the rest of the new items.
                	for (; new_index < new_list.length; new_index++) {
                	    var option=document.createElement("option");
                	    option.text=new_list[new_index];
                		com_port_select.add(option, null); // add to end of list			
                	}
                	break;
        		} else if (new_index >= new_list.length) {
        			// remove any remaining items from select list
        			while(select_index < com_port_select.options.length) {
        				com_port_select.remove(select_index); 
        			}
        			break;
        		} 
        		// start comparing current values
        		var new_value = new_list[new_index];
        		var select_value = com_port_select.options[select_index].value;
        		if (select_value == new_value) {
        			// matching value, increment both counters
        			new_index++;
        			select_index++;
        		} else if (select_value > new_value) {
        			// new value to insert into select
            	    var option=document.createElement("option");
            	    option.text=new_value;
            		com_port_select.add(option, com_port_select.options[select_index++]);
            		new_index++;
        		} else if (select_value < new_value) {
        			// need to remove value from the select list
        			com_port_select.remove(select_index);
        		}
        	}
		}
	},
	"console": {
		"send": function(data) {
	        if (data) {
				dojo.xhrPost( {
		            url: "/xig_console",
		            content: {data: data+'\r\n'},
		            handleAs: "json",
		            preventCache: true
		        });
				// display the data in the output window
		        data = data.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
				dojo.byId('console-output').innerHTML += '<br/><span class="input-color">'+data+'<br/></span>';
				// clear the input command.
				dojo.byId('console-input').value = '';
				xig.console.scroll();
	        }
		},
		"update": function() {
	        dojo.xhrGet( {
	            url: "/xig_console",
	            handleAs: "json",
	            load: xig.console.handler,
	            preventCache: true
	        });
		},
		"handler": function(data) {
			data = data.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
					   .replace(/\r\n/g, "<br/>").replace(/\r/g, "<br/>").replace(/\n/g, "<br/>");
			dojo.byId('console-output').innerHTML += '<span class="output-color">'+data+'</span>';
			xig.console.scroll();
		},
		"scroll": function() {
			// scroll the window to the bottom to see the new output
			var output_div = dojo.byId('console-output');
			output_div.scrollTop = output_div.scrollHeight;
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
	            load: xig.logs.handler,
	            preventCache: true
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
		},
		"add": function(record) {
			// record is an object with the following parameters: 
			// msg: the actual message (required)
			// levelname: string of one of the following: DEBUG, INFO, WARNING, ERROR (defaults to WARNING)
			// name: name of the logger - will default to "webpage"
			// asctime: a timestamp in string format that will default to now
			if (typeof record.msg == "undefined") {
				// bad error msg...  time for a popup
				alert("Received a logging message that wasn't formatted properly");
				return;
			}
			// set the ID
			record.id = xig.logs.id;
			xig.logs.id = xig.logs.id + 1;
			if (typeof record.levelname == "undefined") {
				record.levelname = "WARNING";
			}
			if (typeof record.name == "undefined") {
				record.name = "webpage";
			}
			if (typeof record.asctime == "undefined") {
				var now = new Date();
				var d = now.toDateString(); // Mon Apr 09 2012
				var t = now.toLocaleTimeString(); // 15:45:11
				// combine to get - Mon Apr 09 15:45:11 2012
				record.asctime = d.slice(0, -4) + t + d.slice(-5);
			}
    		// add record to store and save store
			xig.logs.store.newItem(record);
			xig.logs.store.save();
		}
	}
};