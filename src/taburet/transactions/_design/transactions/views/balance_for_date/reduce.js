function(keys, values, rereduce) {
	var debet = 0
	var kredit = 0
	values.forEach( function(v) {
		debet += v.debet
		kredit += v.kredit
	})
	return {debet:Math.round(debet * 100.0) / 100.0,
		kredit:Math.round(kredit * 100.0) / 100.0}
}