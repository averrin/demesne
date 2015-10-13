function reloadStylesheets() {
    var queryString = '?reload=' + new Date().getTime();
    jQuery('link[rel="stylesheet"]').each(function () {
        this.href = this.href.replace(/\?.*|$$/, queryString);
    });
}