function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		var date = new Date(doc.date)
		doc.from_acc.forEach(function(e) {
			emit([date.getFullYear(), date.getMonth() + 1, date.getDate(), e], {kredit:doc.amount, debet:0})
		})
		doc.to_acc.forEach(function(e) {
			emit([date.getFullYear(), date.getMonth() + 1, date.getDate(), e], {kredit:0, debet:doc.amount})
		})
	}
}