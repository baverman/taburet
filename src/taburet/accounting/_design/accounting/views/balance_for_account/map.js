function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		doc.from_acc.forEach(function(e) {
			emit([e, doc.date[0], doc.date[1], doc.date[2]], {kredit:doc.amount, debet:0})
		})
		doc.to_acc.forEach(function(e) {
			emit([e, doc.date[0], doc.date[1], doc.date[2]], {kredit:0, debet:doc.amount})
		})
	}
}