function deletePublication(id) {
    fetch('/deletePublication', {
        method: 'POST',
        body: JSON.stringify({ id: id }),
    }).then((_res) => {
        window.location.href = '/publications';
    });
}