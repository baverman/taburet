function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		doc.from_acc.forEach(function(e) {
			emit(e, -doc.amount)
		})
		doc.to_acc.forEach(function(e) {
			emit(e, doc.amount)
		})
	}	
}