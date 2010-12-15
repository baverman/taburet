function(keys, values, rereduce) {
	var max = 0
	for(i in values) {
		if ( values[i] > max) {
			max = values[i]
		}
	}
	return max
}