function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		doc.to_acc.forEach(function(e) {
			emit(e, doc.amount)
		})
	}	
}