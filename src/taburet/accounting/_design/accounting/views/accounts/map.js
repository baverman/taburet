function(doc) {
	if ( doc.doc_type == 'Account' ) {
		var parents_count = doc.parents.length
		if ( parents_count > 0 ) {
			emit(doc.parents[parents_count-1], null)
		} else {
			emit('ROOT_ACCOUNT', null)
		}
	}
}