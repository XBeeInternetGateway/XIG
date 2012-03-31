xig = {
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