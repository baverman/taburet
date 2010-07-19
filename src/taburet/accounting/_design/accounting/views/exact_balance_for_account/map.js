function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		emit([doc.from_acc[doc.from_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], {kredit:doc.amount, debet:0})
		emit([doc.to_acc[doc.to_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], {kredit:0, debet:doc.amount})
	}
}