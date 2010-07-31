function(doc) {
	if ( doc.doc_type == 'Transaction' ) {
		emit([2, doc.from_acc[doc.from_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], null)
		emit([1, doc.to_acc[doc.to_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], null)
		emit([3, doc.from_acc[doc.from_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], null)
		emit([3, doc.to_acc[doc.to_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], null)
	}
}