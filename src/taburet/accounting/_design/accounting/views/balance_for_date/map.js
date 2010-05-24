function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		var date = new Date(doc.date)
		doc.from_acc.forEach(function(e) {
			emit([doc.date[0], doc.date[1], doc.date[2], e], {kredit:doc.amount, debet:0})
		})
		doc.to_acc.forEach(function(e) {
			emit([doc.date[0], doc.date[1], doc.date[2], e], {kredit:0, debet:doc.amount})
		})
	}
}