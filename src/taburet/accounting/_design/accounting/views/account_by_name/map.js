function(doc) {
	if ( doc.doc_type == 'Account' ) {
		emit(doc.name, null)
	}
}