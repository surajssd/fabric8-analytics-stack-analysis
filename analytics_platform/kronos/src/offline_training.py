import time

from analytics_platform.kronos.src import config
from analytics_platform.kronos.src.kronos_constants import *
from analytics_platform.kronos.src.kronos_pomegranate import KronosPomegranate
from util.data_store.local_filesystem import LocalFileSystem
from util.data_store.s3_data_store import S3DataStore


def load_eco_to_kronos_dependency_dict(input_kronos_dependency_data_store):
    eco_to_kronos_dependency_dict = dict()

    filenames = input_kronos_dependency_data_store.list_files(KD_OUTPUT_FOLDER)
    for filename in filenames:
        ecosystem = filename.split("/")[-1].split(".")[0].split("_")[-1]
        kronos_dependency_json = input_kronos_dependency_data_store.read_json_file(
            filename=filename)
        kronos_dependency_dict = dict(kronos_dependency_json)
        eco_to_kronos_dependency_dict[ecosystem] = kronos_dependency_dict

    return eco_to_kronos_dependency_dict


def load_eco_to_kronos_dependency_dict_local():
    input_data_store = LocalFileSystem('analytics_platform/data/tusharma-kronos-data')
    eco_to_kronos_dependency_dict = load_eco_to_kronos_dependency_dict(
        input_kronos_dependency_data_store=input_data_store)

    return eco_to_kronos_dependency_dict


def load_eco_to_kronos_dependency_dict_s3():
    input_data_store = S3DataStore(src_bucket_name=config.AWS_KRONOS_BUCKET,
                                   access_key=config.AWS_S3_ACCESS_KEY_ID,
                                   secret_key=config.AWS_S3_SECRET_ACCESS_KEY)
    eco_to_kronos_dependency_dict = load_eco_to_kronos_dependency_dict(
        input_kronos_dependency_data_store=input_data_store)

    return eco_to_kronos_dependency_dict


def load_user_eco_to_co_occerrence_matrix_dict(input_co_occurrence_data_store):
    com_filenames = input_co_occurrence_data_store.list_files(COM_OUTPUT_FOLDER)

    temp_user_eco_to_co_occurrence_matrix_dict = dict()
    user_category_list = list()
    ecosystem_list = list()
    for com_filename in com_filenames:
        user_category = com_filename.split("/")[1]
        if user_category not in user_category_list:
            user_category_list.append(user_category)
        ecosystem = com_filename.split("/")[-1].split(".")[0].split("_")[-1]
        if ecosystem not in ecosystem_list:
            ecosystem_list.append(ecosystem)
        co_occurrence_matrix = input_co_occurrence_data_store.read_json_file_into_pandas_df(com_filename)
        temp_user_eco_to_co_occurrence_matrix_dict[
            (user_category, ecosystem)] = co_occurrence_matrix

    user_eco_to_co_occurrence_matrix_dict = dict()

    for user_category in user_category_list:
        eco_to_co_occurrence_matrix_dict = dict()
        for ecosystem in ecosystem_list:
            eco_to_co_occurrence_matrix_dict[ecosystem] = temp_user_eco_to_co_occurrence_matrix_dict[
                (user_category, ecosystem)]
        user_eco_to_co_occurrence_matrix_dict[user_category] = eco_to_co_occurrence_matrix_dict

    return user_eco_to_co_occurrence_matrix_dict


def train_and_save_kronos_list(input_kronos_dependency_data_store, input_co_occurrence_data_store,
                               output_data_store):
    eco_to_kronos_dependency_dict = load_eco_to_kronos_dependency_dict(
        input_kronos_dependency_data_store=input_kronos_dependency_data_store)

    user_eco_to_cooccurrence_matrix_dict = load_user_eco_to_co_occerrence_matrix_dict(
        input_co_occurrence_data_store=input_co_occurrence_data_store)

    for user_category in user_eco_to_cooccurrence_matrix_dict.keys():
        eco_to_cooccurrence_matrix_dict = user_eco_to_cooccurrence_matrix_dict[user_category]
        for ecosystem in eco_to_cooccurrence_matrix_dict.keys():
            kronos_dependency_dict = eco_to_kronos_dependency_dict[ecosystem]
            cooccurrence_matrix_df = eco_to_cooccurrence_matrix_dict[ecosystem]
            kronos_model = KronosPomegranate.train(kronos_dependency_dict=kronos_dependency_dict,
                                                   package_occurrence_df=cooccurrence_matrix_df)
            filename = KRONOS_OUTPUT_FOLDER + "/" + str(user_category) + "/" + "kronos" + "_" + str(
                ecosystem) + ".json"
            kronos_model.save(data_store=output_data_store, filename=filename)


def train_and_save_kronos_list_s3():
    input_kronos_dependency_data_store = S3DataStore(src_bucket_name=config.AWS_KRONOS_BUCKET,
                                                     access_key=config.AWS_S3_ACCESS_KEY_ID,
                                                     secret_key=config.AWS_S3_SECRET_ACCESS_KEY)

    input_cooccurrence_matrix_data_store = S3DataStore(src_bucket_name=config.AWS_KRONOS_BUCKET,
                                                       access_key=config.AWS_S3_ACCESS_KEY_ID,
                                                       secret_key=config.AWS_S3_SECRET_ACCESS_KEY)

    output_data_store = S3DataStore(src_bucket_name=config.AWS_KRONOS_BUCKET,
                                    access_key=config.AWS_S3_ACCESS_KEY_ID,
                                    secret_key=config.AWS_S3_SECRET_ACCESS_KEY)

    train_and_save_kronos_list(input_kronos_dependency_data_store=input_kronos_dependency_data_store,
                               input_co_occurrence_data_store=input_cooccurrence_matrix_data_store,
                               output_data_store=output_data_store)


def train_and_save_kronos_list_local():
    input_kronos_dependency_data_store = LocalFileSystem('analytics_platform/data/tusharma-kronos-data')
    input_cooccurrence_matrix_data_store = LocalFileSystem('analytics_platform/data/tusharma-kronos-data')
    output_data_store = LocalFileSystem('analytics_platform/data/tusharma-kronos-data')

    train_and_save_kronos_list(input_kronos_dependency_data_store=input_kronos_dependency_data_store,
                               input_co_occurrence_data_store=input_cooccurrence_matrix_data_store,
                               output_data_store=output_data_store)


if __name__ == "__main__":
    t0 = time.time()

    train_and_save_kronos_list_s3()
    # train_and_save_kronos_list_local()

    print(time.time() - t0)
