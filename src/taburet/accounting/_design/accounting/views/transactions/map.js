function(doc) {
	if ( doc.doc_type == 'Transaction' ) {
		doc.from_acc.forEach(function(e) {
			emit([e, doc.date[0], doc.date[1], doc.date[2]], null)
		})
		doc.to_acc.forEach(function(e) {
			emit([e, doc.date[0], doc.date[1], doc.date[2]], null)
		})
	}
}