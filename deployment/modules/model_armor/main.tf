resource "google_model_armor_template" "model-armor-template" {
  location    = var.region
  template_id = "agentic-agent-${var.env}-template"
  project     = var.project_id

  # filter_version_selector{
  #   alias = "FILTER_VERSION_ALIAS_STABLE"
  # }


  filter_config {
    dynamic "malicious_uri_filter_settings" {
      for_each = var.enable_malicious_uri_filter ? [1] : []
      content {
        filter_enforcement = "ENABLED"
      }
    }
    # malicious_uri_filter_settings {
    #   filter_enforcement = "ENABLED"
    # }

    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE"
    }
    sdp_settings {
      basic_config {
        filter_enforcement = "ENABLED"
      }
    }
    rai_settings {
      rai_filters {
        filter_type      = "HATE_SPEECH"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "SEXUALLY_EXPLICIT"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "HARASSMENT"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
    }
  }

  dynamic "template_metadata" {
    for_each = var.enable_multi_language_detection ? [1] : []
    content {
      multi_language_detection {
        enable_multi_language_detection = true
      }
    }
  }
  # template_metadata {
  #   multi_language_detection {
  #     enable_multi_language_detection = true
  #   }
  # }
}