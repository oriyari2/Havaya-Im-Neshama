"""Desktop feature composition boundaries.

The existing MVP View/Presenter/Service implementations remain stable.  This
package provides the microfrontend registration façades used by MainWindow so
the shell composes features without wiring their internal signals itself.
"""

from desktop_client.app.features.contracts import FeatureContext, FeatureServices
from desktop_client.app.features.registry import FEATURES, FeatureDescriptor, mount_role_features

__all__ = [
    "FEATURES",
    "FeatureContext",
    "FeatureDescriptor",
    "FeatureServices",
    "mount_role_features",
]
