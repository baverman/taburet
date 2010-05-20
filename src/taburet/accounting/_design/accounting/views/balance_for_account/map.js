function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		var date = new Date(doc.date)
		doc.from_acc.forEach(function(e) {
			emit([e, date.getFullYear(), date.getMonth() + 1, date.getDate()], {kredit:doc.amount, debet:0})
		})
		doc.to_acc.forEach(function(e) {
			emit([e, date.getFullYear(), date.getMonth() + 1, date.getDate()], {kredit:0, debet:doc.amount})
		})
	}
}