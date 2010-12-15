function(doc) {
	if ( doc.doc_type ) {
		emit(doc.doc_type, null)
	}
}