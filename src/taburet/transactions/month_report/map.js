function(doc) {
	if (doc.doc_type && doc.doc_type == 'Transaction') {
		var year = doc.date[0]
		var month = doc.date[1]
		
		if ( year < %(year)d || ( year == %(year)d && month < %(month)d ) ) {
			for each(acc in doc.from_acc) {
				emit(acc, {before: -doc.amount, kredit:0, debet:0})
			}
			for each(acc in doc.to_acc) {
				emit(acc, {before: doc.amount, kredit:0, debet:0})
			}
		} else if ( year == %(year)d && month == %(month)d ) {
			for each(acc in doc.from_acc) {
				emit(acc, {before:0, kredit:doc.amount, debet:0})
			}
			for each(acc in doc.to_acc) {
				emit(acc, {before:0, kredit:0, debet:doc.amount})
			}
		}
	}
}