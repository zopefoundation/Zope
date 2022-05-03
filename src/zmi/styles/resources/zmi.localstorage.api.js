/**
 * $ZMILocalStorageAPI
 * 
 * @see http://fortuito.us/diveintohtml5/storage.html
*/
ZMILocalStorageAPI = function() {
};
ZMILocalStorageAPI.prototype._clear = function(cb) {
	for (var k in localStorage) {
		if (!(k.indexOf("_")==0)) {
			delete localStorage[k];
		}
	}
}
ZMILocalStorageAPI.prototype.keys = function() {
	var l = [];
	for (var k in localStorage) {
		l.push(k);
	}
	l.sort();
	return l;
}
ZMILocalStorageAPI.prototype.get = function(k,d) {
	var v = d;
	var l = this.keys();
	var done = [];
	for (var i=0; i < l.length; i++) {
		var lsk = l[i];
		var nv = null;
		if (lsk.indexOf(k+".")==0) {
			var nk = lsk.substr((k+".").length);
			if (nk.indexOf(".") > 0) {
				nk = nk.substr(0,nk.indexOf("."));
				if ($.inArray(k+"."+nk,done)<0) {
					nv = $ZMILocalStorageAPI.get(k+"."+nk);
					done.push(k+"."+nk);
				}
			}
			else {
				nv = localStorage[lsk];
			}
			if (nv != null) {
				if (isNaN(nk)) {
					if (typeof v == "undefined") {
						v = {};
					}
					v[nk] = nv;
				}
				else {
					if (typeof v == "undefined") {
						v = [];
					}
					v.push(nv);
				}
			}
		}
		else if (lsk==k) {
			nv = localStorage[lsk];
			if (typeof nv != "undefined") {
				v = nv;
			}
		}
	}
	return v;
}
ZMILocalStorageAPI.prototype._set = function(k,v) {
	if (typeof v == "object") {
		if (Array.isArray(v)) {
			for (var i = 0; i < v.length; i++) {
				this._set(k+"."+i,v[i]);
			}
		}
		else {
			for (var i in v) {
				this._set(k+"."+i,v[i]);
			}
		}
	}
	else {
		localStorage[k] = v;
	}
}
ZMILocalStorageAPI.prototype.set = function(k,v,r) {
	this._set(k,v);
	if (r) {
		self.location.reload();
	}
}
ZMILocalStorageAPI.prototype._del = function(k) {
	var l = this.keys();
	for (var i=0; i < l.length; i++) {
		var lsk = l[i];
		if (lsk==k || lsk.indexOf(k+".")==0) {
			delete localStorage[lsk];
		}
	}
}
ZMILocalStorageAPI.prototype.del = function(k,r) {
	this._del(k);
	if (r) {
		self.location.reload();
	}
}
ZMILocalStorageAPI.prototype.toggle = function(k,r) {
	if (this.get(k,null)==null) {
		this.set(k,"1",r);
	}
	else {
		this.del(k,r);
	}
}
ZMILocalStorageAPI.prototype.replace = function(k,v,r) {
	this._del(k);
	this._set(k,v);
	if (r) {
		self.location.reload();
	}
}

$ZMILocalStorageAPI = new ZMILocalStorageAPI();
