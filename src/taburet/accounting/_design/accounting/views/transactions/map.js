function(doc) {
	if ( doc.doc_type == 'Transaction' ) {
		var date = new Date(doc.date)
		doc.from_acc.forEach(function(e) {
			emit([e, date.getFullYear(), date.getMonth() + 1, date.getDate()], null)
		})
		doc.to_acc.forEach(function(e) {
			emit([e, date.getFullYear(), date.getMonth() + 1, date.getDate()], null)
		})
	}
}