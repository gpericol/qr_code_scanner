function copyImage(id) {
    fetch($("#"+id).attr('data')).then((response) => {
        response.blob().then(function(result) {
            navigator.clipboard.write([
            new ClipboardItem({
                [result.type]: result
            })
            ]);
        });
    })
    console.log('Image copied.');
};