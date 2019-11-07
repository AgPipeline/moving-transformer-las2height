"""Transformer for calculating plant height from as las file
"""
import copy
import datetime
import logging
import os
import laspy
import numpy as np

import terrautils.lemnatec

import configuration
import transformer_class

terrautils.lemnatec.SENSOR_METADATA_CACHE = os.path.dirname(os.path.realpath(__file__))


class __internal__():
    """Class for internal use only functions
    """

    def __init__(self):
        """Initializes class instance
        """

    @staticmethod
    def cleanup_request_md(source_md: dict) -> dict:
        """Makes a copy of the source metadata and cleans it up for use as plot-level information
        Arguments:
            source_md: the source metadata to clone and clean up
        Returns:
            returns the cleaned up metadata
        """
        if not source_md:
            return {}

        new_md = copy.deepcopy(source_md)
        new_md.pop('list_files', None)
        new_md.pop('context_md', None)
        new_md.pop('working_folder', None)

        return new_md

    @staticmethod
    def prepare_container_md(plot_name: str, plot_md: dict, key_name: str, source_file: str, result_files: list) -> dict:
        """Prepares the metadata for a single container
        Arguments:
            plot_name: the name of the container
            plot_md: the metadata associated with this container
            key_name: the name of the key related to the files
            source_file: the name of the source file
            result_files: list of files to add to container metadata
        Return:
            The formatted metadata
        Notes:
            The files in result_files are checked for existence before being added to the metadata
        """
        cur_md = {
            'name': plot_name,
            'metadata': {
                'replace': True,
                'data': plot_md
            },
            'file': []
        }
        for one_file in result_files:
            if os.path.exists(one_file):
                cur_md['file'].append({
                    'path': one_file,
                    'key': key_name,
                    'metadata': {
                        'source': source_file,
                        'transformer': configuration.TRANSFORMER_NAME,
                        'version': configuration.TRANSFORMER_VERSION,
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'plot_name': plot_name
                    }
                })
        return cur_md


def get_traits_table() -> tuple:
    """Returns the traits table information
    Return:
        Returns a tuple consisting of a list field names, and trait dictionary.
    """
    # Compiled traits table
    fields = ('local_datetime', 'canopy_height', 'access_level', 'species', 'site',
              'citation_author', 'citation_year', 'citation_title', 'method')
    traits = {'local_datetime' : '',
              'canopy_height' : [],
              'access_level': '2',
              'species': 'Sorghum bicolor',
              'site': [],
              'citation_author': '"Zongyang, Li"',
              'citation_year': '2016',
              'citation_title': 'Maricopa Field Station Data and Metadata',
              'method': 'Scanner 3d ply data to height'}

    return (fields, traits)


def generate_traits_list(traits: dict) -> list:
    """Returns a list of trait values
    Arguments:
        traits: a dict containing the current trait data
    Return:
        A list of trait data
    """
    # compose the summary traits
    trait_list = [traits['local_datetime'],
                  traits['canopy_height'],
                  traits['access_level'],
                  traits['species'],
                  traits['site'],
                  traits['citation_author'],
                  traits['citation_year'],
                  traits['citation_title'],
                  traits['method']
                  ]

    return trait_list


def las_to_height(in_file: str, out_histogram_file: str = None) -> tuple:
    """Return a tuple of (height histogram, max height) from an LAS file.
    Arguments:
        in_file: the source LAS file
        out_histogram_file: optional output file for the histogram data
    Return:
        A tuple of the height histogram and the maximum found height
    """
    number_of_bins = 500
    height_hist = np.zeros(number_of_bins)

    las_handle = laspy.file.File(in_file)
    z_data = las_handle.Z

    if z_data.size == 0:
        logging.info("No height data was loaded from las file: %s", in_file)
        return height_hist, None

    max_height = np.max(z_data)
    height_hist = np.histogram(z_data, bins=number_of_bins, density=False)[0]

    if out_histogram_file:
        with open(out_histogram_file, 'w') as out_file:
            out_file.write("bin,height_cm,count\n")
            for idx, height in enumerate(height_hist):
                out_file.write("%s,%s,%s\n" % (idx+1, "%s-%s" % (idx, idx+1), height))

    return height_hist, max_height


def perform_process(transformer: transformer_class.Transformer, check_md: dict, transformer_md: dict, full_md: dict) -> dict:
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
        check_md: request specific metadata
        transformer_md: metadata from previous runs of this transformer
        full_md: the full request metadata
    Return:
        Returns a dictionary with the results of processing
    """
    # pylint: disable=unused-argument
    # Prepare local variables
    start_timestamp = datetime.datetime.now()
    plot_name = check_md['context_md'].get('plot_name')
    if plot_name is None:
        return {'code': -1000, 'error': "Plot name is missing from request metadata"}

    # We only work with the first las file we find
    container_md = []
    maximum = 0
    for one_file in check_md['list_files']():
        if not os.path.splitext(one_file)[1].lower() == '.las':
            continue

        out_path = os.path.join(check_md['working_folder'], plot_name)
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        filename_base = os.path.splitext(os.path.basename(one_file))[0]
        hist_csv = os.path.join(out_path, filename_base + '_histogram.csv')
        out_csv = os.path.join(out_path, filename_base + '_canopyheight_bety.csv')

        logging.debug("Calling las_to_height with source: '%s'", one_file)
        logging.debug("    output histogram file: '%s'", str(hist_csv))
        (_, maximum) = las_to_height(one_file, hist_csv)

        if maximum is None:
            msg = "LAS file has no height data: %s" % one_file
            logging.warning(msg)
            return {'code': 0, 'message': msg}

        with open(out_csv, 'w') as csv_file:
            (fields, traits) = get_traits_table()
            csv_file.write(','.join(map(str, fields)) + '\n')
            traits['canopy_height'] = str(maximum)
            traits['site'] = plot_name
            traits['local_datetime'] = check_md['timestamp']
            trait_list = generate_traits_list(traits)
            csv_file.write(','.join(map(str, trait_list)) + '\n')

        # Prep the metadata for return
        plot_md = __internal__.cleanup_request_md(check_md)
        plot_md['plot_name'] = plot_name

        container_md.append(
            __internal__.prepare_container_md(plot_name, plot_md, configuration.TRANSFORMER_TYPE, one_file, [hist_csv, out_csv])
        )

        # We're only processing one file
        break

    if container_md:
        return {
            'code': 0,
            'container': container_md,
            configuration.TRANSFORMER_NAME:
            {
                'utc_timestamp': datetime.datetime.utcnow().isoformat(),
                'processing_time': str(datetime.datetime.now() - start_timestamp),
                'canopy_height': str(maximum)
            }
        }

    return {'code': 0, 'message': "No LAS files were detected in the list of files to process"}
