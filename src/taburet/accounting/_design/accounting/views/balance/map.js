function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		doc.from_acc.forEach(function(e) {
			emit(e, {kredit:doc.amount, debet:0})
		})
		doc.to_acc.forEach(function(e) {
			emit(e, {kredit:0, debet:doc.amount})
		})
	}
}