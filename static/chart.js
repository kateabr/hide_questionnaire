function random_rgba_value(offset) {
    return offset + Math.floor(Math.random() * (255 - offset * 2));
}

class RGBA {
    constructor(r, g, b) {
        this.r = r;
        this.g = g;
        this.b = b;
    }

    fillAlpha(alpha) {
        return 'rgba(' + this.r + ',' + this.g + ',' + this.b + ',' + alpha + ')';
    }

    offsetAndFillAlpha(offset, alpha) {
        return 'rgba(' + (this.r - offset) + ',' + (this.g - offset) + ',' + (this.b - offset) + ',' + alpha + ')';
    }

    toString() {
        return '(' + this.r + ',' + this.g + ',' + this.b + ')';
    }

}

class RandomRGBAColorsList {
    constructor(length, offset) {
        var temp = [];

        for (var i = 0; i < length; i++) {
            temp.push(new RGBA(random_rgba_value(offset), random_rgba_value(offset), random_rgba_value(offset)));
        }

        this.colors = temp;
        this.offset = offset;
    }

    fillAlpha(alpha) {
        var colors_to_return = [];
        for (var i = 0; i < this.colors.length; i++) {
            colors_to_return.push(this.colors[i].fillAlpha(alpha));
        }

        return colors_to_return;
    }

    offsetAndFillAlpha(alpha) {
        var colors_to_return = [];
        for (var i = 0; i < this.colors.length; i++) {
            colors_to_return.push(this.colors[i].offsetAndFillAlpha(this.offset, alpha));
            colors_to_return.push(this.colors[i].offsetAndFillAlpha(-this.offset, alpha));
        }

        return colors_to_return;
    }
}

function renderChart(languages, languages_distr, sexes, sex_distr) {
    var ctx = document.getElementById('stats');

    var colors = new RandomRGBAColorsList(languages.length, 50);

    var lang_colors = colors.fillAlpha(0.5);
    var lang_brim_colors = colors.fillAlpha(1);
    var sex_colors = colors.offsetAndFillAlpha(0.7);
    var sex_brim_colors = colors.offsetAndFillAlpha(1);

    var myChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: languages,
            datasets: [
                {
                    labels: languages,
                    data: languages_distr,
                    backgroundColor: lang_colors,
                    borderColor: lang_brim_colors,
                    borderWidth: 1
                },
                {
                    labels: sexes,
                    data: sex_distr,
                    backgroundColor: sex_colors,
                    borderColor: sex_brim_colors,
                    borderWidth: 1,
                }
            ]
        },
        options: {
            title: {
                display: true,
                text: 'Answers language- and sex-wise',
                fontSize: 20
            },
            plugins: {
                labels: {
                    render: 'percentage'
                }
            },
            tooltips: {
                callbacks: {
                    label: function (tooltipItem, data) {
                        var label = data.datasets[tooltipItem.datasetIndex].labels[tooltipItem.index];
                        var value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
                        return label + ': ' + value;
                    },

                },
            },
            legend: {
                onClick: null
            },
            cutoutPercentage: 20,
        }
    });
}