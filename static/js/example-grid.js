$(function() {

    var bytesToText = function(sizeInBytes) {
        var bytes = sizeInBytes;
        if (typeof(bytes) == 'undefined') { return '' }
        var sizes = ['B','KB','MB','GB','TB']
        var unit = 0
        while(bytes > 1024) {
            bytes = bytes / 1024;
            unit++
        }
        return bytes.toFixed(unit < 2 ? unit : 2)
            + " " + sizes[unit]

    }

    var isNumeric = function(n) { return !isNaN(parseFloat(n)) && isFinite(n); }

    var formatSize = function(row, cell, value, columnDef, dataContext) {
        if (isNumeric(dataContext['size'])) {
            return bytesToText(dataContext['size'])
        } else {
            return '--'
        }
    }

    var indentByDepth = function(row, cell, value, columnDef, dataContext) {
        var indent = (
            dataContext['depth'] > 1
            ? 10 * dataContext['depth'] - 1
            : 0 );
        var text = (
            dataContext['depth'] == 0
                ? dataContext['name']
                : '⌞ ' + dataContext['name'] );

        var obj = $('<span></span>')
        obj.css('padding-left', indent);
        obj.text(text); // .text() escapes
        obj.addClass(
            'hgrid-' + ( dataContext['type'] || 'none' )
        );
        return obj[0].outerHTML
    }

    // Defined as a function so this can be used later to refresh the grid
    //  (this is a convention, not necessary for hGrid)
    var get_items = function() { return $.ajax({ 'method': 'GET', 'url': '/api/files/', 'async': false}).responseJSON['files']; };

    // Initialize the grid

    // The following line turns off PyCharm's type validation for this line.
    //noinspection JSValidateTypes
    myGrid = HGrid.create({
        // CSS selector to the DOM element that will be the grid.
        container: "#exampleGrid",
        // The data itself - the name should and likely will be changed
        info: get_items(),
        // column definition
        columns:[
            {
                id: "name",
                name: "Name",
                field: "name",
                cssClass: "cell-title",
                sortable: true,
                defaultSortAsc: true,
                formatter: indentByDepth
            },
            {
                id: "size",
                name: "Size",
                field: "size",
                width: 90,
                sortable: true,
                formatter: formatSize
            }
        ],
        enableCellNavigation: false,
        autoHeight: true,
        forceFitColumns: true,
        largeGuide: false,
        dropZonePreviewsContainer: false,
        // Necessary to make drag-n-drop uploads work
        dropZone: true,
        // Used as dropzone's POST endpoint.
        // May also be specified as "url"
        url: '/api/files/'
    });

    // Adds an extra column at the end containing the "delete" button.
    myGrid.Slick.grid.setColumns(
        myGrid.options.columns.concat(
            {
                id: "buttons",
                name: 'Actions',
                // A formatter is a special method that allows the developer to
                // specify the exact text of the cell.
                formatter: function(row, cell, value, columnDef, dataContext) {
                    return "<a href='#' onclick='myGrid.deleteItems([\"" +
                        dataContext['uid'] +
                        "\"])' class='btn btn-danger deleteBtn'>Delete</a>";
                }
            }
        )
    );

    myGrid.hGridBeforeDelete.subscribe(function(e, args) {
        var ids = [];

        for (var item in args['items']) {
            ids.push(args['items'][item]['uid'])
        }

        // Send a list of IDs to delete to the backend.
        // example:
        //  { 'ids': ['foo', 'bar', 'baz' ] }
        $.ajax({
            'type': 'DELETE',
            'url': '/api/files/',
            'data': {'ids': JSON.stringify(ids)}
        })
    });

    myGrid.hGridAfterUpload.subscribe(function(e, args){
        // After an item is uploaded, update the grid.
        myGrid.uploadItem(args['item'])
    });

    myGrid.hGridBeforeMove.subscribe(function(e, args) {
        console.log(args);
        return false
    })


})