function(keys, values, rereduce) {
	return Math.round(sum(values) * 100.0) / 100.0
}