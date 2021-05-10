from os import path

def my_plot_export(fig,
                   axs,
                   name,
                   fontsize=10,
                   dpi=300,
                   width=5.5,
                   height=3.5,
                   directory='plots'):

    fig.set_size_inches(w=width, h=height)
    fig.set_dpi(dpi)

    for ax in axs:
        for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                     ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(fontsize)

    # Save and remove excess whitespace
    fig.savefig(path.join(directory, name + '.pdf'),
                format='pdf',
                bbox_inches='tight')
