# coding: utf-8

"""
    EcoTaxa

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.25
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from to_back.ecotaxa_cli_py.configuration import Configuration


class ProjectUserStatsModel(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'projid': 'int',
        'annotators': 'list[MinimalUserBO]',
        'activities': 'list[UserActivity]'
    }

    attribute_map = {
        'projid': 'projid',
        'annotators': 'annotators',
        'activities': 'activities'
    }

    def __init__(self, projid=None, annotators=None, activities=None, local_vars_configuration=None):  # noqa: E501
        """ProjectUserStatsModel - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._projid = None
        self._annotators = None
        self._activities = None
        self.discriminator = None

        if projid is not None:
            self.projid = projid
        if annotators is not None:
            self.annotators = annotators
        if activities is not None:
            self.activities = activities

    @property
    def projid(self):
        """Gets the projid of this ProjectUserStatsModel.  # noqa: E501

        The project id.  # noqa: E501

        :return: The projid of this ProjectUserStatsModel.  # noqa: E501
        :rtype: int
        """
        return self._projid

    @projid.setter
    def projid(self, projid):
        """Sets the projid of this ProjectUserStatsModel.

        The project id.  # noqa: E501

        :param projid: The projid of this ProjectUserStatsModel.  # noqa: E501
        :type: int
        """

        self._projid = projid

    @property
    def annotators(self):
        """Gets the annotators of this ProjectUserStatsModel.  # noqa: E501

        The users who ever decided on classification or state of objects.  # noqa: E501

        :return: The annotators of this ProjectUserStatsModel.  # noqa: E501
        :rtype: list[MinimalUserBO]
        """
        return self._annotators

    @annotators.setter
    def annotators(self, annotators):
        """Sets the annotators of this ProjectUserStatsModel.

        The users who ever decided on classification or state of objects.  # noqa: E501

        :param annotators: The annotators of this ProjectUserStatsModel.  # noqa: E501
        :type: list[MinimalUserBO]
        """

        self._annotators = annotators

    @property
    def activities(self):
        """Gets the activities of this ProjectUserStatsModel.  # noqa: E501

        More details on annotators' activities.  # noqa: E501

        :return: The activities of this ProjectUserStatsModel.  # noqa: E501
        :rtype: list[UserActivity]
        """
        return self._activities

    @activities.setter
    def activities(self, activities):
        """Sets the activities of this ProjectUserStatsModel.

        More details on annotators' activities.  # noqa: E501

        :param activities: The activities of this ProjectUserStatsModel.  # noqa: E501
        :type: list[UserActivity]
        """

        self._activities = activities

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, ProjectUserStatsModel):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, ProjectUserStatsModel):
            return True

        return self.to_dict() != other.to_dict()