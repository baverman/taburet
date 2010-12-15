function(doc) {
	var parts = doc._id.split("-")
	if ( parts.length == 2 ) {
		var num = parseInt(parts[1])
		if ( !isNaN(num) ) {
			emit(parts[0], num)
		}
	}
}