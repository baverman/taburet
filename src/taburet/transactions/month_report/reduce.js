function(keys, values, rereduce) {
	var debet = 0
	var kredit = 0
	var before = 0
	
	for each(v in values) {
		if ( v.before === undefined) { 
			debet += v.debet
			kredit += v.kredit
		} else {
			before += v.before
		}
	}
	
	return {debet:Math.round(debet * 100.0) / 100.0,
		kredit:Math.round(kredit * 100.0) / 100.0,
		before:Math.round(before * 100.0) / 100.0,
		after:Math.round((before + debet - kredit) * 100.0) / 100.0
	}
}